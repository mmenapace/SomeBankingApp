from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import random
import string
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from fastapi.middleware.cors import CORSMiddleware



# --- Database Setup ---

DATABASE_URL = "sqlite:///./bank.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Database Models ---


class TransactionType(str, Enum):
    IBAN_TRANSFER = "IBAN_TRANSFER"
    CARD_RECHARGE = "CARD_RECHARGE"
    CARD_PAYMENT = "CARD_PAYMENT"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

    accounts = relationship("BankAccount", back_populates="owner")
    cards = relationship("RechargeableCard", back_populates="owner")


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    iban = Column(String(34), unique=True, index=True, nullable=False)
    balance = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    owner = relationship("User", back_populates="accounts")


class RechargeableCard(Base):
    __tablename__ = "rechargeable_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_number = Column(String(16), unique=True, index=True, nullable=False)
    cvv = Column(String(3), nullable=False)
    expiry_month = Column(Integer, nullable=False)
    expiry_year = Column(Integer, nullable=False)
    balance = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    is_active = Column(SAEnum("ACTIVE", "BLOCKED", name="card_status"), default="ACTIVE")

    owner = relationship("User", back_populates="cards")


class TransactionLog(Base):
    __tablename__ = "transaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    tx_type = Column(SAEnum(TransactionType), nullable=False)
    source_identifier = Column(String, nullable=False)
    destination_identifier = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---


class UserCreate(BaseModel):
    full_name: str
    email: str


class AccountResponse(BaseModel):
    id: int
    iban: str
    balance: Decimal

    class Config:
        from_attributes = True


class CardCreate(BaseModel):
    user_id: int


class CardResponse(BaseModel):
    id: int
    card_number: str
    expiry_month: int
    expiry_year: int
    balance: Decimal
    is_active: str

    class Config:
        from_attributes = True


class IBANTransferRequest(BaseModel):
    sender_iban: str
    receiver_iban: str
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: Optional[str] = "IBAN Transfer"


class CardRechargeRequest(BaseModel):
    card_number: str
    source_iban: str
    amount: Decimal = Field(gt=0, decimal_places=2)


class CardPaymentRequest(BaseModel):
    card_number: str
    cvv: str
    expiry_month: int
    expiry_year: int
    merchant_name: str
    amount: Decimal = Field(gt=0, decimal_places=2)


# --- Helper Generators ---


def generate_iban(country_code="DE") -> str:
    random_digits = "".join(random.choices(string.digits, k=18))
    return f"{country_code}89{random_digits}"


def generate_card_number() -> str:
    return "4000" + "".join(random.choices(string.digits, k=12))


# --- FastAPI Application ---

app = FastAPI(title="Simple Banking Backend API", version="1.0.0")

# Add this right after app = FastAPI(...) in your Python code:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/users/", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(full_name=payload.full_name, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Automatically provision a checking account with a generated IBAN
    initial_account = BankAccount(
        user_id=user.id,
        iban=generate_iban(),
        balance=Decimal("1000.00"),  # Starter balance for testing
    )
    db.add(initial_account)
    db.commit()
    return {"user_id": user.id, "name": user.full_name, "iban": initial_account.iban}


@app.get("/accounts/{iban}", response_model=AccountResponse)
def get_account_balance(iban: str, db: Session = Depends(get_db)):
    account = db.query(BankAccount).filter(BankAccount.iban == iban).first()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return account


@app.post("/transfers/iban", status_code=status.HTTP_200_OK)
def transfer_via_iban(transfer: IBANTransferRequest, db: Session = Depends(get_db)):
    if transfer.sender_iban == transfer.receiver_iban:
        raise HTTPException(status_code=400, detail="Sender and receiver IBAN cannot be identical")

    sender = db.query(BankAccount).filter(BankAccount.iban == transfer.sender_iban).with_for_update().first()
    receiver = db.query(BankAccount).filter(BankAccount.iban == transfer.receiver_iban).with_for_update().first()

    if not sender:
        raise HTTPException(status_code=404, detail="Sender IBAN does not exist")
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver IBAN does not exist")
    if sender.balance < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Atomic state mutation
    sender.balance -= transfer.amount
    receiver.balance += transfer.amount

    log = TransactionLog(
        tx_type=TransactionType.IBAN_TRANSFER,
        source_identifier=sender.iban,
        destination_identifier=receiver.iban,
        amount=transfer.amount,
        description=transfer.description,
    )
    db.add(log)
    db.commit()

    return {
        "status": "success",
        "message": f"Transferred {transfer.amount} to {receiver.iban}",
        "new_balance": sender.balance,
    }


@app.post("/cards/issue", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def issue_rechargeable_card(payload: CardCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_card = RechargeableCard(
        user_id=user.id,
        card_number=generate_card_number(),
        cvv="".join(random.choices(string.digits, k=3)),
        expiry_month=12,
        expiry_year=2028,
        balance=Decimal("0.00"),
        is_active="ACTIVE",
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return new_card


@app.post("/cards/recharge", status_code=status.HTTP_200_OK)
def recharge_card(payload: CardRechargeRequest, db: Session = Depends(get_db)):
    account = db.query(BankAccount).filter(BankAccount.iban == payload.source_iban).with_for_update().first()
    card = db.query(RechargeableCard).filter(RechargeableCard.card_number == payload.card_number).with_for_update().first()

    if not account:
        raise HTTPException(status_code=404, detail="Funding bank account not found")
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    if card.is_active != "ACTIVE":
        raise HTTPException(status_code=400, detail="Cannot recharge an inactive or blocked card")
    if account.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds in bank account")

    # Transfer funds from bank account into prepaid card
    account.balance -= payload.amount
    card.balance += payload.amount

    log = TransactionLog(
        tx_type=TransactionType.CARD_RECHARGE,
        source_identifier=account.iban,
        destination_identifier=card.card_number,
        amount=payload.amount,
        description="Prepaid card top-up",
    )
    db.add(log)
    db.commit()

    return {
        "status": "success",
        "card_number": card.card_number[-4:].rjust(16, "*"),
        "recharged_amount": payload.amount,
        "new_card_balance": card.balance,
        "remaining_account_balance": account.balance,
    }


@app.post("/cards/pay", status_code=status.HTTP_200_OK)
def make_card_payment(payment: CardPaymentRequest, db: Session = Depends(get_db)):
    card = db.query(RechargeableCard).filter(RechargeableCard.card_number == payment.card_number).with_for_update().first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.is_active != "ACTIVE":
        raise HTTPException(status_code=400, detail="Card is blocked or inactive")

    # Card verification check
    if (
        card.cvv != payment.cvv
        or card.expiry_month != payment.expiry_month
        or card.expiry_year != payment.expiry_year
    ):
        raise HTTPException(status_code=400, detail="Invalid card verification details")

    # Balance check
    if card.balance < payment.amount:
        raise HTTPException(status_code=400, detail="Declined: Insufficient card balance")

    # Process deduction
    card.balance -= payment.amount

    log = TransactionLog(
        tx_type=TransactionType.CARD_PAYMENT,
        source_identifier=card.card_number,
        destination_identifier=payment.merchant_name,
        amount=payment.amount,
        description=f"POS Payment to {payment.merchant_name}",
    )
    db.add(log)
    db.commit()

    return {
        "status": "approved",
        "merchant": payment.merchant_name,
        "amount_paid": payment.amount,
        "remaining_card_balance": card.balance,
    }


@app.get("/transactions/audit")
def list_transactions(db: Session = Depends(get_db)):
    logs = db.query(TransactionLog).order_by(TransactionLog.timestamp.desc()).limit(50).all()
    return logs
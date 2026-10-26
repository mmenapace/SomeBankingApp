export interface UserCreate {
  full_name: string;
  email: string;
}

export interface UserResponse {
  user_id: number;
  name: string;
  iban: string;
}

export interface IBANTransfer {
  sender_iban: string;
  receiver_iban: string;
  amount: number;
  description?: string;
}

export interface CardCreate {
  user_id: number;
}

export interface CardResponse {
  id: number;
  card_number: string;
  expiry_month: number;
  expiry_year: number;
  balance: number;
  is_active: string;
}

export interface CardRecharge {
  card_number: string;
  source_iban: string;
  amount: number;
}

export interface CardPayment {
  card_number: string;
  cvv: string;
  expiry_month: number;
  expiry_year: number;
  merchant_name: string;
  amount: number;
}

export interface TransactionLog {
  id: number;
  tx_type: string;
  source_identifier: string;
  destination_identifier: string;
  amount: number;
  description: string;
  timestamp: string;
}
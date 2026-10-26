import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { 
  UserCreate, UserResponse, IBANTransfer, CardCreate, 
  CardResponse, CardRecharge, CardPayment, TransactionLog 
} from '../models/bank.models';

@Injectable({
  providedIn: 'root'
})
export class BankService {
  // Ensure your FastAPI app is running on this URL
  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  createUser(user: UserCreate): Observable<UserResponse> {
    return this.http.post<UserResponse>(`${this.apiUrl}/users/`, user);
  }

  transferIban(transfer: IBANTransfer): Observable<any> {
    return this.http.post(`${this.apiUrl}/transfers/iban`, transfer);
  }

  issueCard(card: CardCreate): Observable<CardResponse> {
    return this.http.post<CardResponse>(`${this.apiUrl}/cards/issue`, card);
  }

  rechargeCard(recharge: CardRecharge): Observable<any> {
    return this.http.post(`${this.apiUrl}/cards/recharge`, recharge);
  }

  payWithCard(payment: CardPayment): Observable<any> {
    return this.http.post(`${this.apiUrl}/cards/pay`, payment);
  }

  getLogs(): Observable<TransactionLog[]> {
    return this.http.get<TransactionLog[]>(`${this.apiUrl}/transactions/audit`);
  }
}
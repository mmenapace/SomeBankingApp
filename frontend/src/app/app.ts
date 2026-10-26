import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { BankService } from './core/services/bank.services';
import { TransactionLog } from './core/models/bank.models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './app.html',
  styleUrls: ['./app.scss']
})
export class AppComponent implements OnInit {
  // Forms
  userForm: FormGroup;
  transferForm: FormGroup;
  cardForm: FormGroup;
  rechargeForm: FormGroup;
  paymentForm: FormGroup;

  // State
  logs: TransactionLog[] = [];
  feedbackMessage: string | null = null;

  constructor(private fb: FormBuilder, private bankService: BankService) {
    this.userForm = this.fb.group({
      full_name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]]
    });

    this.transferForm = this.fb.group({
      sender_iban: ['', Validators.required],
      receiver_iban: ['', Validators.required],
      amount: [0, [Validators.required, Validators.min(0.01)]],
      description: ['IBAN Transfer']
    });

    this.cardForm = this.fb.group({
      user_id: ['', Validators.required]
    });

    this.rechargeForm = this.fb.group({
      card_number: ['', Validators.required],
      source_iban: ['', Validators.required],
      amount: [0, [Validators.required, Validators.min(0.01)]]
    });

    this.paymentForm = this.fb.group({
      card_number: ['', Validators.required],
      cvv: ['', Validators.required],
      expiry_month: ['', [Validators.required, Validators.min(1), Validators.max(12)]],
      expiry_year: ['', Validators.required],
      merchant_name: ['', Validators.required],
      amount: [0, [Validators.required, Validators.min(0.01)]]
    });
  }

  ngOnInit() {
    this.loadLogs();
  }

  loadLogs() {
    this.bankService.getLogs().subscribe(
      (data: TransactionLog[]) => this.logs = data,
      (err: any) => console.error('Failed to load logs', err)
    );
  }

  showMessage(msg: string) {
    this.feedbackMessage = msg;
    setTimeout(() => this.feedbackMessage = null, 5000);
  }

  createUser() {
    if (this.userForm.valid) {
      this.bankService.createUser(this.userForm.value).subscribe({
        next: (res: { iban: any; }) => {
          this.showMessage(`User Created! IBAN: ${res.iban}`);
          this.userForm.reset();
        },
        error: (err: { error: { detail: any; }; }) => this.showMessage(`Error: ${err.error.detail}`)
      });
    }
  }

  transferIban() {
    if (this.transferForm.valid) {
      this.bankService.transferIban(this.transferForm.value).subscribe({
        next: () => {
          this.showMessage('Transfer Successful!');
          this.transferForm.reset();
          this.loadLogs();
        },
        error: (err: { error: { detail: any; }; }) => this.showMessage(`Error: ${err.error.detail}`)
      });
    }
  }

  issueCard() {
    if (this.cardForm.valid) {
      this.bankService.issueCard(this.cardForm.value).subscribe({
        next: (res: { card_number: any; }) => {
          this.showMessage(`Card Issued! Number: ${res.card_number}`);
          this.cardForm.reset();
        },
        error: (err: { error: { detail: any; }; }) => this.showMessage(`Error: ${err.error.detail}`)
      });
    }
  }

  rechargeCard() {
    if (this.rechargeForm.valid) {
      this.bankService.rechargeCard(this.rechargeForm.value).subscribe({
        next: () => {
          this.showMessage('Card Recharged Successfully!');
          this.rechargeForm.reset();
          this.loadLogs();
        },
        error: (err: { error: { detail: any; }; }) => this.showMessage(`Error: ${err.error.detail}`)
      });
    }
  }

  makePayment() {
    if (this.paymentForm.valid) {
      this.bankService.payWithCard(this.paymentForm.value).subscribe({
        next: () => {
          this.showMessage('Payment Approved!');
          this.paymentForm.reset();
          this.loadLogs();
        },
        error: (err: { error: { detail: any; }; }) => this.showMessage(`Error: ${err.error.detail}`)
      });
    }
  }
}
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../../../services/auth.service';
import { UserService } from '../../../services/user.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.css']
})
export class ProfileComponent implements OnInit {

  user: any;
  profileForm!: FormGroup;
  successMessage: string = '';
  errorMessage: string = '';

  constructor(
    private authService: AuthService,
    private userService: UserService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.user = this.authService.getCurrentUser();
    this.initForm();
  }

  initForm() {
    this.profileForm = this.fb.group({
      nom: [this.user.nom, Validators.required],
      email: [this.user.email, [Validators.required, Validators.email]],
      password: ['']
    });
  }

  saveProfile() {
    if (this.profileForm.invalid) return;

    const updatedData = this.profileForm.value;

    this.userService.updateUser(this.user.id, updatedData).subscribe({
      next: (res: any) => {
        this.successMessage = 'Profil mis à jour avec succès !';
        this.errorMessage = '';
        this.user = res;
      },
      error: () => {
        this.errorMessage = 'Erreur lors de la mise à jour du profil.';
        this.successMessage = '';
      }
    });
  }
}

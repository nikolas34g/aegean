import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReviewsService } from '../services/reviews.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home {
  url = '';
  model = 'gemini';
  reviews: any[] = [];
  loading = false;

  constructor(private reviewsService: ReviewsService) {}

  runAnalysis() {
    if (!this.url) {
      alert('Please enter a Google Maps URL');
      return;
    }

    this.loading = true;
    this.reviewsService.analyzeReviews(this.url, this.model).subscribe({
      next: (data) => {
        this.reviews = data;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.loading = false;
      },
    });
  }
}

// import { Component } from '@angular/core';
// import { HttpClient } from '@angular/common/http';
// import { environment } from '../../environments/environment';
// import { CommonModule } from '@angular/common';
// import { ReviewsService } from '../services/reviews.service';
// @Component({
//   selector: 'app-home',
//   imports: [CommonModule],
//   templateUrl: './home.html',
//   styleUrl: './home.css'
// })
// export class Home {
//   reviews: any[] = [];
//   loading: boolean = false;

//   constructor(private reviewsService: ReviewsService) {}

//   fetchReviews() {
//     this.loading = true;
//     this.reviewsService.getReviews().subscribe({
//       next: (data) => {
//         this.reviews = data;
//         this.loading = false;
//       },
//       error: (error) => {
//         console.error('Error fetching reviews', error);
//         this.loading = false;
//       },
//     });
//   }
// }


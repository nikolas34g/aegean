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
  comparisonData: any[] = [];     
  modelSummaries: any = {}; 
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


  runComparison() {
    if (!this.url) {
      alert('Please enter a Google Maps URL');
      return;
    }

    this.loading = true;
    this.reviewsService.compareModels(this.url).subscribe({
      next: (data) => {
        this.comparisonData = data.comparisons;
        this.modelSummaries = data.summary;
        this.reviews = []; // clear single model results if switching
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.loading = false;
      },
    });
  }

}


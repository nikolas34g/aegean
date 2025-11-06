import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReviewsService } from '../services/reviews.service';
import { FormsModule } from '@angular/forms';
import { ChartOptions, ChartData } from 'chart.js';
import { BaseChartDirective, provideCharts, withDefaultRegisterables } from 'ng2-charts';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule, BaseChartDirective],
  providers: [provideCharts(withDefaultRegisterables())],
  templateUrl: './home.html',
  styleUrls: ['./home.css'],
})
export class Home {
  url = '';
  model = 'gemini';
  reviews: any[] = [];
  comparisonData: any[] = [];
  modelSummaries: any = {};
  loading = false;

  plots: any = null;

  // Toggles
  showSingleModelSummary = false;
  showReviews = false;
  showGeminiSummary = false;
  showHfSummary = false;
  showCombinedSummary = false;

  mode: 'single' | 'compare' | null = null; // track mode

  sentimentChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  ratingsChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  chartOptions: ChartOptions<'bar'> = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Sentiment Analysis Charts' },
    },
  };

  singleModelSummary: string = '';

constructor(private reviewsService: ReviewsService) {
  // Load saved state from localStorage on component init
  const savedState = localStorage.getItem('reviewAppState');
  if (savedState) {
    const state = JSON.parse(savedState);
    this.url = state.url || '';
    this.model = state.model || 'gemini';
    this.reviews = state.reviews || [];
    this.comparisonData = state.comparisonData || [];
    this.modelSummaries = state.modelSummaries || {};
    this.singleModelSummary = state.singleModelSummary || '';
    this.mode = state.mode || null;
    this.plots = state.plots || null;
  }
}

// Helper function to save state
private saveState() {
  const state = {
    url: this.url,
    model: this.model,
    reviews: this.reviews,
    comparisonData: this.comparisonData,
    modelSummaries: this.modelSummaries,
    singleModelSummary: this.singleModelSummary,
    mode: this.mode,
    plots: this.plots
  };
  localStorage.setItem('reviewAppState', JSON.stringify(state));
}

runAnalysis() {
  if (!this.url) {
    alert('Please enter a Google Maps URL');
    return;
  }

  // Clear old state for a new analysis
  localStorage.removeItem('reviewAppState');

  this.loading = true;
  this.reviewsService.analyzeReviews(this.url, this.model).subscribe({
    next: (data) => {
      this.reviews = data.reviews || [];
      this.singleModelSummary = data.summary || '';
      this.showSingleModelSummary = false;
      this.showReviews = false;

      this.comparisonData = [];
      this.mode = 'single';
      this.plots = null;

      this.saveState(); // save new state
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

  // Clear old state for a new comparison
  localStorage.removeItem('reviewAppState');

  this.loading = true;
  this.reviewsService.compareModels(this.url).subscribe({
    next: (data) => {
      this.comparisonData = data.comparisons || [];
      this.modelSummaries = data.summary || {};
      this.reviews = [];
      this.showReviews = false;
      this.showGeminiSummary = false;
      this.showHfSummary = false;
      this.showCombinedSummary = false;
      this.mode = 'compare';

      this.plots = data.plots;

      if (this.plots) {
        this.sentimentChartData = {
          labels: Object.keys(this.plots.sentiment_counts.gemini),
          datasets: [
            {
              label: 'Gemini',
              data: Object.values(this.plots.sentiment_counts.gemini),
              backgroundColor: 'rgba(54, 162, 235, 0.6)',
            },
            {
              label: 'HuggingFace',
              data: Object.values(this.plots.sentiment_counts.huggingface),
              backgroundColor: 'rgba(255, 99, 132, 0.6)',
            },
          ],
        };

        this.ratingsChartData = {
          labels: Object.keys(this.plots.ratings_counts),
          datasets: [
            {
              label: 'Star Ratings',
              data: Object.values(this.plots.ratings_counts),
              backgroundColor: 'rgba(75, 192, 192, 0.6)',
            },
          ],
        };
      }

      this.saveState(); // save new state
      this.loading = false;
    },
    error: (err) => {
      console.error(err);
      this.loading = false;
    },
  });
}

}

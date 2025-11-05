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

  constructor(private reviewsService: ReviewsService) {}

  runAnalysis() {
    if (!this.url) {
      alert('Please enter a Google Maps URL');
      return;
    }

    this.loading = true;
    this.reviewsService.analyzeReviews(this.url, this.model).subscribe({
      next: (data) => {
        this.reviews = data.reviews || [];
        this.singleModelSummary = data.summary || '';
        this.showSingleModelSummary = false;
        this.showReviews = false;

        this.comparisonData = [];
        this.mode = 'single';
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

        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.loading = false;
      },
    });
  }

  getKeys(obj: any) {
    return obj ? Object.keys(obj) : [];
  }
}

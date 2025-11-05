import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ReviewsService {
  private baseUrl = 'http://160.40.51.142:8000'; // FastAPI URL

  constructor(private http: HttpClient) {}

  analyzeReviews(url: string, model: string): Observable<any[]> {
    return this.http.post<any[]>(`${this.baseUrl}/analyze`, { url, model });
  }

  compareModels(url: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/compare`, { url });
  }
}


// import { Injectable } from '@angular/core';
// import { HttpClient } from '@angular/common/http';
// import { Observable } from 'rxjs';
// import { environment } from '../../environments/environment';

// @Injectable({
//   providedIn: 'root',
// })
// export class ReviewsService {
//   private apiUrl = environment.apiUrl;

//   constructor(private http: HttpClient) {}

//   getReviews(): Observable<any[]> {
//     return this.http.get<any[]>(this.apiUrl);
//   }
// }


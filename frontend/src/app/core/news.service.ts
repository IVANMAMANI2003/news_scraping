import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface NewsItem {
  id: number;
  titulo?: string | null;
  fecha?: string | null;
  hora?: string | null;
  resumen?: string | null;
  contenido?: string | null;
  categoria?: string | null;
  autor?: string | null;
  tags?: string | null;
  url?: string | null;
  fecha_extraccion?: string | null;
  imagenes?: string | string[] | null;
  fuente?: string | null;
  created_at?: string | null;
}

@Injectable({ providedIn: 'root' })
export class NewsService {
  private readonly apiBase = '/api';
  constructor(private http: HttpClient) {}

  getAll(): Observable<NewsItem[]> {
    return this.http.get<any>(`${this.apiBase}/news`).pipe(
      map((res) => Array.isArray(res) ? res as NewsItem[] : (res && Array.isArray(res.items) ? res.items as NewsItem[] : []))
    );
  }

  getById(id: number | string): Observable<NewsItem> {
    return this.http.get<NewsItem>(`${this.apiBase}/news/${id}`);
  }
}

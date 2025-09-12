import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NewsItem, NewsService } from '../../core/news.service';

@Component({
  selector: 'app-category',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './category.component.html',
  styleUrl: './category.component.css'
})
export class CategoryComponent {
  private readonly newsService = inject(NewsService);
  private readonly route = inject(ActivatedRoute);
  fuente = '';
  categoria = '';
  news: NewsItem[] = [];

  constructor() {
    this.route.queryParamMap.subscribe(params => {
      this.fuente = params.get('fuente') || '';
      this.categoria = params.get('categoria') || '';
      this.load();
    });
  }

  load() {
    this.newsService.getAll().subscribe(items => {
      let list = items || [];
      if (this.fuente) list = list.filter(n => (n.fuente || '').toLowerCase() === this.fuente.toLowerCase());
      if (this.categoria) list = list.filter(n => (n.categoria || '').toLowerCase() === this.categoria.toLowerCase());
      this.news = list;
    });
  }

  parseImages(item: NewsItem): string[] {
    const raw = Array.isArray(item.imagenes) ? item.imagenes.join('\n') : (item.imagenes || '');
    return String(raw)
      .split(/\||,|;|\n|\s+/)
      .map(s => s.trim())
      .filter(Boolean);
  }
}

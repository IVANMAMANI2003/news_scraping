import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NewsItem, NewsService } from '../../core/news.service';

@Component({
  selector: 'app-single',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './single.component.html',
  styleUrl: './single.component.css'
})
export class SingleComponent {
  private readonly newsService = inject(NewsService);
  private readonly route = inject(ActivatedRoute);
  item?: NewsItem;

  constructor() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.newsService.getById(id).subscribe(n => this.item = n);
      }
    });
  }

  parseImages(item?: NewsItem): string[] {
    if (!item) return [];
    const raw = Array.isArray(item.imagenes) ? item.imagenes.join('\n') : (item.imagenes || '');
    return String(raw)
      .split(/\||,|;|\n|\s+/)
      .map(s => s.trim())
      .filter(Boolean);
  }
}

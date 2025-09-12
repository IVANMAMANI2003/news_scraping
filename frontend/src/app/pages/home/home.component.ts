import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NewsItem, NewsService } from '../../core/news.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent implements AfterViewInit {
  private readonly newsService = inject(NewsService);
  news: NewsItem[] = [];
  loading = true;
  error = '';

  constructor() {
    this.fetch();
  }

  fetch(): void {
    this.loading = true;
    this.error = '';
    this.newsService.getAll().subscribe({
      next: (items) => {
        this.news = Array.isArray(items) ? items : [];
        this.loading = false;
        setTimeout(() => this.initCarousels(), 0);
      },
      error: (err) => {
        this.loading = false;
        this.error = 'No se pudo cargar noticias del API';
        this.news = [];
      }
    });
  }

  parseImages(item: NewsItem): string[] {
    const raw = Array.isArray(item.imagenes) ? item.imagenes.join('\n') : (item.imagenes || '');
    return String(raw)
      .split(/\||,|;|\n|\s+/)
      .map(s => s.trim())
      .filter(Boolean);
  }

  ngAfterViewInit(): void {
    this.initCarousels();
  }

  private initCarousels(): void {
    const $ = (window as any).jQuery || (window as any).$;
    if (!$) return;
    try {
      const main = $('.main-carousel');
      if (main && main.owlCarousel) {
        main.owlCarousel({ autoplay: true, smartSpeed: 1500, items: 1, dots: true, loop: true, center: true });
      }
      const trending = $('.tranding-carousel');
      if (trending && trending.owlCarousel) {
        trending.owlCarousel({ autoplay: true, smartSpeed: 2000, items: 1, dots: false, loop: true, nav: true, navText: ['<i class="fa fa-angle-left"></i>','<i class="fa fa-angle-right"></i>'] });
      }
      const featured = $('.news-carousel');
      if (featured && featured.owlCarousel) {
        featured.owlCarousel({ autoplay: true, smartSpeed: 1000, margin: 30, dots: false, loop: true, nav: true, navText: ['<i class="fa fa-angle-left" aria-hidden="true"></i>','<i class="fa fa-angle-right" aria-hidden="true"></i>'], responsive: { 0:{items:1},576:{items:1},768:{items:2},992:{items:3},1200:{items:4} } });
      }
    } catch (_) {}
  }
}

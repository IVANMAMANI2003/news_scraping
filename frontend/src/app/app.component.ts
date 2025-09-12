import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { NewsService } from './core/news.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'frontend';
  private readonly newsService = inject(NewsService);
  fuentes: string[] = [];
  categoriasPorFuente: Record<string, string[]> = {};

  constructor() {
    this.newsService.getAll().subscribe(items => {
      const map = new Map<string, Set<string>>();
      (items || []).forEach(n => {
        const fuente = (n.fuente || 'Otros').trim();
        const categoria = (n.categoria || 'Sin categoría').trim();
        if (!map.has(fuente)) map.set(fuente, new Set<string>());
        map.get(fuente)!.add(categoria);
      });
      this.fuentes = Array.from(map.keys()).sort();
      this.categoriasPorFuente = {};
      for (const [f, set] of map.entries()) this.categoriasPorFuente[f] = Array.from(set.values()).sort();
    });
  }
}

import { Component, ElementRef, Inject, PLATFORM_ID, ViewChild } from '@angular/core';
import { DomSanitizer, Title, Meta } from '@angular/platform-browser';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../api.service';
import { MESSAGES_HE, SearchManager } from '../searcher';
import { FormsModule } from '@angular/forms';
import { marked } from 'marked';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-mobile',
  imports: [
    RouterModule,
    FormsModule,
  ],
  templateUrl: './mobile.component.html',
  styleUrl: './mobile.component.less'
})
export class MobileComponent {
  @ViewChild('input') input: ElementRef<HTMLInputElement> | null = null;

  searcher: SearchManager;

  constructor(private api: ApiService, private sanitizer: DomSanitizer, 
              private route: ActivatedRoute, private router: Router, 
              private title: Title, private meta: Meta, @Inject(PLATFORM_ID) private platformId: Object
            ) {
    const renderer = new marked.Renderer();
    const linkRenderer = renderer.link;
    renderer.link = (href: string, title: string, text: string) => {
      if (isPlatformBrowser(platformId)) {
        const localLink = href.startsWith(`${location.protocol}//${location.hostname}`);
        const html = linkRenderer.call(renderer, href, title, text);
        return localLink ? html : html.replace(/^<a /, `<a target="_top" rel="noreferrer noopener nofollow" `);  
      } else {
        return linkRenderer.call(renderer, href, title, text);
      }
    };
    marked.use({renderer});        
    this.searcher = new SearchManager(
      this.api,
      this.router,
      this.route,
      this.sanitizer,
      this.title, 
      this.meta,
      ['/m'],
      MESSAGES_HE,
    );
  }

  ngAfterViewInit() {
    if (this.input) {
      this.searcher.inputElement = this.input.nativeElement;
    }
  }

  keydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      this.searcher.ask();
    }
  }
}

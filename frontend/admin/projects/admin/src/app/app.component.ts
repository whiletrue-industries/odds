import { Component, signal } from '@angular/core';
import { LayoutComponent } from "./layout/layout.component";
import { marked } from 'marked';
import utcPlugin from 'dayjs/plugin/utc';
import dayjs from 'dayjs';

dayjs.extend(utcPlugin);
@Component({
  selector: 'app-root',
  imports: [LayoutComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.less'
})
export class AppComponent {
  constructor() {
    const renderer = new marked.Renderer();
    const linkRenderer = renderer.link;
    renderer.link = (href: string, title: string, text: string) => {
      const localLink = href.startsWith(`${location.protocol}//${location.hostname}`);
      const html = linkRenderer.call(renderer, href, title, text);
      return localLink ? html : html.replace(/^<a /, `<a target="_blank" rel="noreferrer noopener nofollow" `);
    };
    marked.use({renderer});
  }
}
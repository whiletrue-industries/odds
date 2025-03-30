import { AfterViewInit, Directive, ElementRef, Renderer2 } from '@angular/core';

// If the attached element contains more than 50% hebrew characters, set the direction to rtl

@Directive({
  selector: '[rtlize]',
  standalone: true
})
export class RtlizeDirective implements AfterViewInit {

  constructor(private el: ElementRef, private renderer: Renderer2) { }

  ngAfterViewInit(): void {
    const elementText = this.el.nativeElement.textContent || '';
    const hebrewCharCount = (elementText.match(/[\u0590-\u05FF]/g) || []).length;
    const totalCharCount = elementText.length;

    if (totalCharCount > 0 && hebrewCharCount / totalCharCount > 0.25) {
      this.renderer.setStyle(this.el.nativeElement, 'direction', 'rtl');
      this.renderer.setStyle(this.el.nativeElement, 'text-align', 'right');
    }
  }
}
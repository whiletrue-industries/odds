import { Component, Input, signal } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-quality-score',
  imports: [
    MatIconModule
  ],
  templateUrl: './quality-score.component.html',
  styleUrl: './quality-score.component.less'
})
export class QualityScoreComponent {

  @Input() qualityScore: number = 0;
  @Input() size = 18;

  score = signal<number>(0);

  ngOnChanges() {
    let score = this.qualityScore / 20 + 1;
    if (score > 5) {
      score = 5;
    }
    if (score < 1) {
      score = 1;
    }
    this.score.set(score);
  }
}

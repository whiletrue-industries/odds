import { Component, computed, effect, EventEmitter, Input, Output, signal } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { debounceTime, distinctUntilChanged, startWith, Subject } from 'rxjs';
import { StateService } from '../state.service';

@Component({
  selector: 'app-text-filter',
  imports: [
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    ReactiveFormsModule,
  ],
  templateUrl: './text-filter.component.html',
  styleUrl: './text-filter.component.less'
})
export class TextFilterComponent {

  @Input() kind: string = 'text';

  searchText = signal<string | null>(null);
  searchSubject = new Subject<string | null>();
  focused = signal(false);
  placeholder = computed(() => {
    if (this.focused()) {
      return 'Full text search on all fields...';
    } else {
      return `Filter ${this.kind}...`;
    }
  });

  constructor(private state: StateService) {
    effect(() => {
      this.searchSubject.next(this.searchText());
    });
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      startWith(null)
    ).subscribe((searchText) => {
      state.textFilter.set(searchText)
    });
  }
}

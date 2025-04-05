import { Component, computed, DestroyRef, effect, Input, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { debounceTime, distinctUntilChanged, startWith, Subject } from 'rxjs';
import { PageState, StateService } from '../state.service';

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
export class TextFilterComponent implements OnInit {

  @Input() kind: string = 'text';
  @Input() pageState: PageState;

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

  constructor(private state: StateService, private destroyRef: DestroyRef) {
    effect(() => {
      this.searchSubject.next(this.searchText());
    });
  }
  
  ngOnInit() {
    this.searchSubject.pipe(
      takeUntilDestroyed(this.destroyRef),
      debounceTime(300),
      distinctUntilChanged(),
      startWith(null)
    ).subscribe((searchText) => {
      this.pageState.textFilter.set(searchText)
    });
  }
}

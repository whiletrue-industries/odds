import { isPlatformBrowser, isPlatformServer } from '@angular/common';
import { Inject, Injectable, PLATFORM_ID } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class PlatformService {

  safari = false;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {
    this.browser(() => {
      if (navigator?.userAgent.indexOf('Safari') != -1 && 
          navigator?.userAgent.indexOf('Chrome') == -1) {
        this.safari = true;
      }
    });
  }

  browser<T>(callable?: () => void): boolean {
    if (isPlatformBrowser(this.platformId)) {
      if (callable) {
        callable();
      }
      return true;
    }
    return false;
  }

  server<T>(callable?: () => void): boolean {
    if (isPlatformServer(this.platformId)) {
      if (callable) {
        callable();
      }
      return true;
    }
    return false;
  }
}

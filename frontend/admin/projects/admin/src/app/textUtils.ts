export function ellipsizeText(text: string, maxLength: number = 100): string {
  if (text?.length > maxLength) {
    return text.substring(0, maxLength) + '…';
  }
  return text;
}

/**
 * Utility function to merge class names (similar to clsx)
 */

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}


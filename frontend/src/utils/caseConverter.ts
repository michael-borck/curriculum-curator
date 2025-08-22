/**
 * Utility functions for converting between snake_case and camelCase
 */

/**
 * Convert snake_case to camelCase
 */
export function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Convert camelCase to snake_case
 */
export function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

/**
 * Convert object keys from snake_case to camelCase recursively
 */
export function convertKeysToCamelCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => convertKeysToCamelCase(item)) as any;
  }

  if (typeof obj === 'object' && obj.constructor === Object) {
    const converted: any = {};
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        const camelKey = snakeToCamel(key);
        converted[camelKey] = convertKeysToCamelCase(obj[key]);
      }
    }
    return converted;
  }

  return obj;
}

/**
 * Convert object keys from camelCase to snake_case recursively
 */
export function convertKeysToSnakeCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => convertKeysToSnakeCase(item)) as any;
  }

  if (typeof obj === 'object' && obj.constructor === Object) {
    const converted: any = {};
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        const snakeKey = camelToSnake(key);
        converted[snakeKey] = convertKeysToSnakeCase(obj[key]);
      }
    }
    return converted;
  }

  return obj;
}

/**
 * Wrapper for API responses to automatically convert snake_case to camelCase
 */
export function transformResponse<T = any>(data: any): T {
  return convertKeysToCamelCase<T>(data);
}

/**
 * Wrapper for API requests to automatically convert camelCase to snake_case
 */
export function transformRequest<T = any>(data: any): T {
  return convertKeysToSnakeCase<T>(data);
}

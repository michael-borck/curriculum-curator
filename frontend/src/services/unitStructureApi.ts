/**
 * Barrel re-export for Unit Structure API modules.
 *
 * Individual modules live in their own files; this file exists so that
 * existing `import { xxxApi } from '.../unitStructureApi'` statements
 * continue to work unchanged.
 */

export { learningOutcomesApi } from './learningOutcomesApi';
export { materialsApi } from './materialsApi';
export { assessmentsApi } from './assessmentsApi';
export { analyticsApi } from './analyticsApi';
export { accreditationApi } from './accreditationApi';

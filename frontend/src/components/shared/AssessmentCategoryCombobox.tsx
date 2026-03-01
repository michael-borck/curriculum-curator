import {
  getCategoryMeta,
  ALL_KNOWN_CATEGORIES,
} from '../../constants/assessmentCategories';
import { MetadataCombobox } from './MetadataCombobox';

interface AssessmentCategoryComboboxProps {
  value: string;
  onChange: (value: string) => void;
  sectorId?: string | undefined;
}

export function AssessmentCategoryCombobox({
  value,
  onChange,
  sectorId,
}: AssessmentCategoryComboboxProps) {
  return (
    <MetadataCombobox
      value={value}
      onChange={onChange}
      sectorId={sectorId}
      getMeta={getCategoryMeta}
      allItems={ALL_KNOWN_CATEGORIES}
      getSectorDefaults={p => p.defaultAssessmentCategories}
      searchPlaceholder='Search categories...'
      customPlaceholder='Enter custom category name'
      noResultsLabel='No matching categories'
      allItemsLabel='All categories'
    />
  );
}

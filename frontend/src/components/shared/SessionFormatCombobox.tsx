import {
  getFormatMeta,
  ALL_KNOWN_FORMATS,
} from '../../constants/sessionFormats';
import { MetadataCombobox } from './MetadataCombobox';

interface SessionFormatComboboxProps {
  value: string;
  onChange: (value: string) => void;
  sectorId?: string | undefined;
}

export function SessionFormatCombobox({
  value,
  onChange,
  sectorId,
}: SessionFormatComboboxProps) {
  return (
    <MetadataCombobox
      value={value}
      onChange={onChange}
      sectorId={sectorId}
      getMeta={getFormatMeta}
      allItems={ALL_KNOWN_FORMATS}
      getSectorDefaults={p => p.defaultSessionFormats}
      searchPlaceholder='Search formats...'
      customPlaceholder='Enter custom format name'
      noResultsLabel='No matching formats'
      allItemsLabel='All formats'
    />
  );
}

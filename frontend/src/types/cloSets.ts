export interface CLOItem {
  id: string;
  cloSetId: string;
  code: string;
  description: string;
  orderIndex: number;
  createdAt: string;
  updatedAt: string;
}

export interface CLOSet {
  id: string;
  userId: string;
  name: string;
  description?: string;
  programCode?: string;
  items: CLOItem[];
  createdAt: string;
  updatedAt: string;
}

export interface CLOSetCreate {
  name: string;
  description?: string;
  programCode?: string;
}

export interface CLOSetUpdate {
  name?: string;
  description?: string;
  programCode?: string;
}

export interface CLOItemCreate {
  code: string;
  description: string;
  orderIndex?: number;
}

export interface CLOItemUpdate {
  code?: string;
  description?: string;
  orderIndex?: number;
}

export interface ULOCLOMapping {
  id: string;
  uloId: string;
  cloItemId: string;
  isAiSuggested: boolean;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface BulkULOCLOMappingCreate {
  cloItemIds: string[];
  isAiSuggested?: boolean;
}

export interface CLOSuggestionPair {
  uloId: string;
  cloItemId: string;
}

export interface CLOSuggestionsResponse {
  suggestions: CLOSuggestionPair[];
  message: string;
}

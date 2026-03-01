import { useState } from 'react';
import { Search, Link2, Bookmark } from 'lucide-react';
import SearchPanel from './SearchPanel';
import UrlExtractPanel from './UrlExtractPanel';
import SavedSourcesPanel from './SavedSourcesPanel';

type Tab = 'search' | 'urls' | 'saved';

const ResearchPage = () => {
  const [activeTab, setActiveTab] = useState<Tab>('search');

  return (
    <div className='p-6 max-w-5xl mx-auto'>
      <div className='mb-6'>
        <h1 className='text-2xl font-bold text-gray-900'>Research</h1>
        <p className='text-gray-600 mt-1'>
          Search academic sources or import URLs to scaffold units, compare
          coverage, or build reading lists.
        </p>
      </div>

      {/* Tabs */}
      <div className='border-b border-gray-200 mb-6'>
        <nav className='flex gap-6'>
          <button
            onClick={() => setActiveTab('search')}
            className={`pb-3 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === 'search'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Search className='w-4 h-4' />
            Search
          </button>
          <button
            onClick={() => setActiveTab('urls')}
            className={`pb-3 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === 'urls'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Link2 className='w-4 h-4' />
            Import URLs
          </button>
          <button
            onClick={() => setActiveTab('saved')}
            className={`pb-3 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === 'saved'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Bookmark className='w-4 h-4' />
            Saved Sources
          </button>
        </nav>
      </div>

      {/* Tab content */}
      <div className='bg-white rounded-lg shadow-md p-6'>
        {activeTab === 'search' && <SearchPanel />}
        {activeTab === 'urls' && <UrlExtractPanel />}
        {activeTab === 'saved' && <SavedSourcesPanel />}
      </div>
    </div>
  );
};

export default ResearchPage;

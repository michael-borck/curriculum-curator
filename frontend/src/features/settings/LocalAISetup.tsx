import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Cpu,
  Download,
  CheckCircle,
  XCircle,
  Loader2,
  HardDrive,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Trash2,
  AlertTriangle,
} from 'lucide-react';
import ollamaApi from '../../services/ollamaApi';
import type {
  OllamaStatus,
  OllamaRecommendation,
  PullProgress,
  OllamaTestResult,
} from '../../types/ollama';

interface LocalAISetupProps {
  onComplete: () => void;
  onCancel: () => void;
}

type WizardStep = 'status' | 'select' | 'download' | 'test';

const CURATED_MODELS = [
  { value: 'tinyllama', label: 'TinyLlama (1.1B)', size: '~637 MB', minRam: 2 },
  { value: 'llama3.2', label: 'Llama 3.2 (3B)', size: '~2 GB', minRam: 8 },
  { value: 'mistral', label: 'Mistral (7B)', size: '~4.1 GB', minRam: 16 },
  { value: 'llama3.1', label: 'Llama 3.1 (8B)', size: '~4.7 GB', minRam: 16 },
];

const LocalAISetup: React.FC<LocalAISetupProps> = ({
  onComplete,
  onCancel,
}) => {
  const [step, setStep] = useState<WizardStep>('status');
  const [status, setStatus] = useState<OllamaStatus | null>(null);
  const [recommendation, setRecommendation] =
    useState<OllamaRecommendation | null>(null);
  const [selectedModel, setSelectedModel] = useState('');
  const [isChecking, setIsChecking] = useState(true);
  const [pullProgress, setPullProgress] = useState<PullProgress | null>(null);
  const [pullPercent, setPullPercent] = useState(0);
  const [pullError, setPullError] = useState('');
  const [testResult, setTestResult] = useState<OllamaTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const checkStatus = useCallback(async () => {
    setIsChecking(true);
    try {
      const [statusData, recData] = await Promise.all([
        ollamaApi.getStatus(),
        ollamaApi.getRecommendation(),
      ]);
      setStatus(statusData);
      setRecommendation(recData);
      setSelectedModel(recData.recommended_model);
    } catch {
      setStatus({ available: false, models: [], recommended: '' });
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  const handlePull = () => {
    setPullError('');
    setPullProgress(null);
    setPullPercent(0);

    abortRef.current = ollamaApi.pullModel(
      selectedModel,
      (progress: PullProgress) => {
        setPullProgress(progress);
        if (progress.total && progress.completed) {
          setPullPercent(
            Math.round((progress.completed / progress.total) * 100)
          );
        }
      },
      (error: string) => {
        setPullError(error);
      },
      () => {
        setPullPercent(100);
        setStep('test');
      }
    );
  };

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await ollamaApi.testModel(selectedModel);
      setTestResult(result);
    } catch {
      setTestResult({
        success: false,
        error: 'Test request failed',
        model: selectedModel,
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleActivate = () => {
    onComplete();
  };

  const handleCancelPull = () => {
    abortRef.current?.abort();
    setPullError('');
    setPullProgress(null);
    setPullPercent(0);
  };

  const renderStatusStep = () => (
    <div className='space-y-6'>
      <div className='text-center'>
        <Cpu className='w-12 h-12 mx-auto text-blue-600 mb-3' />
        <h3 className='text-lg font-semibold text-gray-900'>
          Checking Ollama Connection
        </h3>
        <p className='text-sm text-gray-600 mt-1'>
          Ollama provides local AI models that run entirely on your machine.
        </p>
      </div>

      {isChecking ? (
        <div className='flex justify-center py-8'>
          <Loader2 className='w-8 h-8 animate-spin text-blue-600' />
        </div>
      ) : status?.available ? (
        <div className='bg-green-50 border border-green-200 rounded-lg p-4'>
          <div className='flex items-start gap-3'>
            <CheckCircle className='w-5 h-5 text-green-600 mt-0.5' />
            <div>
              <p className='font-medium text-green-800'>Ollama is running</p>
              <p className='text-sm text-green-700 mt-1'>
                {status.models.length > 0
                  ? `${status.models.length} model(s) installed`
                  : 'No models installed yet'}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className='bg-amber-50 border border-amber-200 rounded-lg p-4'>
          <div className='flex items-start gap-3'>
            <AlertTriangle className='w-5 h-5 text-amber-600 mt-0.5' />
            <div>
              <p className='font-medium text-amber-800'>Ollama not detected</p>
              <p className='text-sm text-amber-700 mt-1'>
                Make sure Ollama is running. If using Docker, start with:{' '}
                <code className='bg-amber-100 px-1 rounded text-xs'>
                  docker compose --profile local-ai up
                </code>
              </p>
            </div>
          </div>
        </div>
      )}

      {recommendation && (
        <div className='bg-gray-50 rounded-lg p-4'>
          <div className='flex items-center gap-2 mb-2'>
            <HardDrive className='w-4 h-4 text-gray-500' />
            <span className='text-sm font-medium text-gray-700'>
              System Info
            </span>
          </div>
          <div className='grid grid-cols-2 gap-2 text-sm text-gray-600'>
            <div>Total RAM: {recommendation.total_ram_gb} GB</div>
            <div>Available: {recommendation.available_ram_gb} GB</div>
          </div>
        </div>
      )}

      <div className='flex justify-between'>
        <button
          onClick={onCancel}
          className='px-4 py-2 text-gray-700 hover:text-gray-900'
        >
          Cancel
        </button>
        <button
          onClick={() => setStep('select')}
          disabled={!status?.available}
          className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2'
        >
          Next <ArrowRight className='w-4 h-4' />
        </button>
      </div>
    </div>
  );

  const renderSelectStep = () => (
    <div className='space-y-6'>
      <div className='text-center'>
        <Sparkles className='w-12 h-12 mx-auto text-blue-600 mb-3' />
        <h3 className='text-lg font-semibold text-gray-900'>Choose a Model</h3>
        <p className='text-sm text-gray-600 mt-1'>
          Select an AI model to download. Larger models produce better results
          but need more RAM.
        </p>
      </div>

      {recommendation && (
        <div className='bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800'>
          Recommended: <strong>{recommendation.label}</strong> &mdash;{' '}
          {recommendation.reason}
        </div>
      )}

      <div className='space-y-2'>
        {CURATED_MODELS.map(model => (
          <label
            key={model.value}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedModel === model.value
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            } ${
              recommendation && recommendation.total_ram_gb < model.minRam
                ? 'opacity-50'
                : ''
            }`}
          >
            <input
              type='radio'
              name='model'
              value={model.value}
              checked={selectedModel === model.value}
              onChange={e => setSelectedModel(e.target.value)}
              className='text-blue-600 focus:ring-blue-500'
            />
            <div className='flex-1'>
              <div className='font-medium text-gray-900'>{model.label}</div>
              <div className='text-xs text-gray-500'>
                Size: {model.size} &middot; Min RAM: {model.minRam} GB
              </div>
            </div>
            {recommendation?.recommended_model === model.value && (
              <span className='px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full'>
                Recommended
              </span>
            )}
          </label>
        ))}
      </div>

      {/* Show already installed models */}
      {status && status.models.length > 0 && (
        <div>
          <h4 className='text-sm font-medium text-gray-700 mb-2'>
            Installed Models
          </h4>
          <div className='space-y-1'>
            {status.models.map(m => (
              <div
                key={m.name}
                className='flex items-center justify-between text-sm bg-gray-50 rounded px-3 py-2'
              >
                <span className='text-gray-700'>{m.name}</span>
                <button
                  onClick={async () => {
                    await ollamaApi.deleteModel(m.name);
                    checkStatus();
                  }}
                  className='text-red-500 hover:text-red-700 p-1'
                  title='Delete model'
                >
                  <Trash2 className='w-3.5 h-3.5' />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className='flex justify-between'>
        <button
          onClick={() => setStep('status')}
          className='px-4 py-2 text-gray-700 hover:text-gray-900 flex items-center gap-2'
        >
          <ArrowLeft className='w-4 h-4' /> Back
        </button>
        <button
          onClick={() => {
            setStep('download');
            handlePull();
          }}
          disabled={!selectedModel}
          className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2'
        >
          <Download className='w-4 h-4' /> Download Model
        </button>
      </div>
    </div>
  );

  const renderDownloadStep = () => (
    <div className='space-y-6'>
      <div className='text-center'>
        <Download className='w-12 h-12 mx-auto text-blue-600 mb-3' />
        <h3 className='text-lg font-semibold text-gray-900'>
          Downloading {selectedModel}
        </h3>
        <p className='text-sm text-gray-600 mt-1'>
          This may take a few minutes depending on your internet speed.
        </p>
      </div>

      <div className='space-y-3'>
        {/* Progress bar */}
        <div className='w-full bg-gray-200 rounded-full h-4 overflow-hidden'>
          <div
            className='h-full bg-blue-600 rounded-full transition-all duration-300'
            style={{ width: `${pullPercent}%` }}
          />
        </div>
        <div className='flex justify-between text-sm text-gray-600'>
          <span>{pullProgress?.status || 'Starting...'}</span>
          <span>{pullPercent}%</span>
        </div>
      </div>

      {pullError && (
        <div className='bg-red-50 border border-red-200 rounded-lg p-4'>
          <div className='flex items-start gap-2'>
            <XCircle className='w-5 h-5 text-red-600 mt-0.5' />
            <div>
              <p className='font-medium text-red-800'>Download failed</p>
              <p className='text-sm text-red-700 mt-1'>{pullError}</p>
            </div>
          </div>
        </div>
      )}

      <div className='flex justify-between'>
        <button
          onClick={() => {
            handleCancelPull();
            setStep('select');
          }}
          className='px-4 py-2 text-gray-700 hover:text-gray-900 flex items-center gap-2'
        >
          <ArrowLeft className='w-4 h-4' /> Cancel
        </button>
        {pullError && (
          <button
            onClick={handlePull}
            className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2'
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );

  const renderTestStep = () => (
    <div className='space-y-6'>
      <div className='text-center'>
        <CheckCircle className='w-12 h-12 mx-auto text-green-600 mb-3' />
        <h3 className='text-lg font-semibold text-gray-900'>
          Model Downloaded
        </h3>
        <p className='text-sm text-gray-600 mt-1'>
          Test the model to make sure it works, then activate it.
        </p>
      </div>

      {!testResult && !isTesting && (
        <button
          onClick={handleTest}
          className='w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium'
        >
          Run Test Generation
        </button>
      )}

      {isTesting && (
        <div className='flex items-center justify-center gap-3 py-4'>
          <Loader2 className='w-5 h-5 animate-spin text-blue-600' />
          <span className='text-sm text-gray-600'>
            Testing model (this may take a moment)...
          </span>
        </div>
      )}

      {testResult && (
        <div
          className={`rounded-lg p-4 ${
            testResult.success
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          <div className='flex items-start gap-2'>
            {testResult.success ? (
              <CheckCircle className='w-5 h-5 text-green-600 mt-0.5' />
            ) : (
              <XCircle className='w-5 h-5 text-red-600 mt-0.5' />
            )}
            <div>
              <p
                className={`font-medium ${
                  testResult.success ? 'text-green-800' : 'text-red-800'
                }`}
              >
                {testResult.success ? 'Test passed' : 'Test failed'}
              </p>
              {testResult.response && (
                <p className='text-sm text-gray-600 mt-1 italic'>
                  &ldquo;{testResult.response}&rdquo;
                </p>
              )}
              {testResult.error && (
                <p className='text-sm text-red-700 mt-1'>{testResult.error}</p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className='flex justify-between'>
        <button
          onClick={() => setStep('select')}
          className='px-4 py-2 text-gray-700 hover:text-gray-900 flex items-center gap-2'
        >
          <ArrowLeft className='w-4 h-4' /> Back
        </button>
        <button
          onClick={handleActivate}
          disabled={!testResult?.success}
          className='px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2'
        >
          <Sparkles className='w-4 h-4' /> Activate Local AI
        </button>
      </div>
    </div>
  );

  const steps: Record<WizardStep, () => React.ReactNode> = {
    status: renderStatusStep,
    select: renderSelectStep,
    download: renderDownloadStep,
    test: renderTestStep,
  };

  const stepOrder: WizardStep[] = ['status', 'select', 'download', 'test'];
  const currentIndex = stepOrder.indexOf(step);

  return (
    <div className='bg-white rounded-lg shadow-lg border border-gray-200 max-w-lg mx-auto'>
      {/* Step indicator */}
      <div className='flex items-center justify-center gap-2 px-6 pt-6 pb-2'>
        {stepOrder.map((s, i) => (
          <React.Fragment key={s}>
            <div
              className={`w-2.5 h-2.5 rounded-full ${
                i <= currentIndex ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            />
            {i < stepOrder.length - 1 && (
              <div
                className={`w-8 h-0.5 ${
                  i < currentIndex ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      <div className='p-6'>{steps[step]()}</div>
    </div>
  );
};

export default LocalAISetup;

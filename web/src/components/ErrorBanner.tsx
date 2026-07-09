// Renders any caught ApiError (or message) in one consistent banner.
import { ApiError } from '../api/client';

export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null;
  const message =
    error instanceof ApiError
      ? `Error ${error.code}: ${error.message}`
      : error instanceof Error
        ? error.message
        : 'Something went wrong';
  return (
    <div role="alert" className="error-banner">
      {message}
    </div>
  );
}

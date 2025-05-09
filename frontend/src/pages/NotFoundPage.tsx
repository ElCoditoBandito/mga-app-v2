
// frontend/src/pages/NotFoundPage.tsx
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Home, ArrowLeft } from 'lucide-react';

const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-10rem)] text-center px-4">
      {/* Adjust min-h if header/footer height changes */}
      <h1 className="text-6xl font-bold text-blue-600 mb-4 tracking-tight">
        404
      </h1>
      <h2 className="text-3xl font-semibold text-slate-800 mb-3 tracking-tight">
        Oops! Page Not Found
      </h2>
      <p className="text-slate-600 mb-8 max-w-md">
        The page you are looking for doesn't exist, has been removed, or you may not have permission to view it.
      </p>
      <div className="flex flex-col sm:flex-row gap-3">
        <Button
          onClick={() => navigate(-1)}
          variant="outline"
          className="bg-white border-slate-300 hover:bg-slate-50 text-slate-700 hover:text-slate-800"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go Back
        </Button>
        <Button asChild className="bg-blue-600 hover:bg-blue-700">
          <Link to="/">
            <Home className="mr-2 h-4 w-4" />
            Go to My Clubs Dashboard
          </Link>
        </Button>
      </div>
    </div>
  );
};

export default NotFoundPage;

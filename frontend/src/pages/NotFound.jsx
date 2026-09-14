
export default function NotFound() {
  return (
    <div className="flex h-screen justify-center items-center bg-gray-50">
      <div className="flex flex-col gap-8 -mt-20">
        <h2 className="text-5xl font-bold text-gray-900">
          Page Not Found - 404
        </h2>
        <p className="text-center text-xl text-gray-800">
          The page you are looking for does not exist.
        </p>
        <div className="text-center">
          <a href="/login" className="text-blue-700">Click here to Login</a>
        </div>
      </div>
    </div>
  );
}

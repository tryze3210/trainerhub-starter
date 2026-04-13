import { LoginForm } from "./login-form";

export const metadata = {
  title: "Login | TrainerHub",
  description: "Sign in to TrainerHub.",
};

export default function LoginPage() {
  return (
    <main className="mx-auto max-w-lg space-y-6 p-8">
      <div>
        <h1 className="text-3xl font-bold">Login</h1>
        <p className="text-slate-600">Use the auth API contract that will later be replaced by real JWT or session auth.</p>
      </div>
      <LoginForm />
    </main>
  );
}

import { RegisterForm } from "./register-form";

export const metadata = {
  title: "Register | TrainerHub",
  description: "Create a TrainerHub account.",
};

export default function RegisterPage() {
  return (
    <main className="mx-auto max-w-lg space-y-6 p-8">
      <div>
        <h1 className="text-3xl font-bold">Register</h1>
        <p className="text-slate-600">Create a user account and receive a session payload.</p>
      </div>
      <RegisterForm />
    </main>
  );
}

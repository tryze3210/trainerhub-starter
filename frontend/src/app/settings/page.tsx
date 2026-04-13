import { accountApi } from "@/lib/api";
import { ProfileForm } from "./profile-form";
import { SettingsForm } from "./settings-form";

export const metadata = {
  title: "Settings | TrainerHub",
  description: "Manage account profile and communication settings.",
};

export default async function SettingsPage() {
  const [profile, settings] = await Promise.all([
    accountApi.profile(),
    accountApi.settings(),
  ]);

  return (
    <main className="mx-auto max-w-5xl space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-slate-600">Profile, locale and communication preferences.</p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        <ProfileForm profile={profile} />
        <SettingsForm settings={settings} />
      </div>
    </main>
  );
}

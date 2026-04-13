export default function HomePage() {
  return (
    <main style={{ padding: 24, fontFamily: "Arial, sans-serif" }}>
      <h1>TrainerHub</h1>
      <p>Production-oriented starter: homepage shell for catalog, blocks and onboarding.</p>
      <ul>
        <li>/trainers — каталог тренеров</li>
        <li>/login — email JWT login</li>
        <li>/register — регистрация customer/trainer</li>
        <li>/trainer/dashboard — кабинет тренера</li>
      </ul>
    </main>
  );
}

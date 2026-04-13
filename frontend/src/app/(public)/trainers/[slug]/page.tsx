type Props = { params: Promise<{ slug: string }> };

export default async function TrainerProfilePage({ params }: Props) {
  const { slug } = await params;
  return (
    <main className="container">
      <h1>Тренер: {slug}</h1>
    </main>
  );
}

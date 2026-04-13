import { contentApi } from "@/lib/api";

export default async function ContentProgramsPage() {
  const items = await contentApi.programs();
  return (
    <main>
      <h1>Published programs</h1>
      <ul>
        {items.map((item) => (
          <li key={item.id}>{item.title} — lessons: {item.lessons.length}</li>
        ))}
      </ul>
    </main>
  );
}

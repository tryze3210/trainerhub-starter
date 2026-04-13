import { contentApi } from "@/lib/api";

export default async function ContentVideosPage() {
  const items = await contentApi.videos();
  return (
    <main>
      <h1>Published videos</h1>
      <ul>
        {items.map((item) => (
          <li key={item.id}>{item.title} — {item.trainer_name}</li>
        ))}
      </ul>
    </main>
  );
}

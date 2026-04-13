import { contentApi } from "@/lib/api";

export default async function ContentBundlesPage() {
  const items = await contentApi.bundles();
  return (
    <main>
      <h1>Published bundles</h1>
      <ul>
        {items.map((item) => (
          <li key={item.id}>{item.title}</li>
        ))}
      </ul>
    </main>
  );
}

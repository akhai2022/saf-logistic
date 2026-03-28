import { redirect } from "next/navigation";

export default function RouteDetailRedirect({ params }: { params: { id: string } }) {
  redirect(`/route-templates/${params.id}`);
}

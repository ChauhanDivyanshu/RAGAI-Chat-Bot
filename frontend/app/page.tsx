import { Sidebar } from "@/components/layout/Sidebar";
import { ChatContainer } from "@/components/chat/ChatContainer";

export default function Home() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0">
        <ChatContainer />
      </main>
    </div>
  );
}

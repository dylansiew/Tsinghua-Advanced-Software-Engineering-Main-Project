import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarProvider,
    SidebarTrigger,
} from "@/components/ui/sidebar";
import { SidebarActions } from "./actions";

interface AppSideBarProviderProps {
  children: React.ReactNode;
}
export const AppSideBarProvider: React.FC<AppSideBarProviderProps> = ({
  children,
}) => {
  return (
    <div className="p-1 w-[100vw]">
      <SidebarProvider>
        <AppSideBar />
        <main className="w-full">
          <SidebarTrigger />
          {children}
        </main>
      </SidebarProvider>
    </div>
  );
};

const AppSideBar = () => {
  return (
    <Sidebar>
      <SidebarHeader></SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarGroupLabel>Application</SidebarGroupLabel>
              {SidebarActions.map((action) => (
                <SidebarMenuItem key={action.name}>
                  <SidebarMenuButton>
                    <a href={action.url}>
                      <span>{action.name}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter></SidebarFooter>
    </Sidebar>
  );
};

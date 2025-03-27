import { Input } from "@/components/ui/input";
import { SearchBarCoin } from "./coins";
import { SearchBarLogo } from "./logo";

export const SearchBar = () => {
  return (
    <div className="w-full flex flex-col gap-5">
      <div className="flex flex-row items-center justify-center">
        <SearchBarLogo />
        <div className="absolute right-10">
          <SearchBarCoin />
        </div>
      </div>
      <Input />
    </div>
  );
};

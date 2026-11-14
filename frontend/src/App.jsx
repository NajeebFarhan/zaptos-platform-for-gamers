import { BrowserRouter, Link, Route, Routes } from "react-router";
import Layout from "./components/Layout";
import Deals from "./pages/Deals";
import GameHub from "./pages/GameHub";
import GuidesHome from "./pages/GuidesHome";
import Home from "./pages/Home";
import Reader from "./pages/Reader";
import Search from "./pages/Search";
import WikiPage from "./pages/WikiPage";
import Wishlist from "./pages/Wishlist";

function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-24 text-center">
      <div className="font-display text-7xl font-bold text-gradient">404</div>
      <p className="mt-3 text-muted">That page respawned somewhere else.</p>
      <Link to="/" className="btn-primary mt-6">Back to base</Link>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="search" element={<Search />} />
          <Route path="deals" element={<Deals />} />
          <Route path="wishlist" element={<Wishlist />} />
          <Route path="guides" element={<GuidesHome />} />
          <Route path="guides/:gameId" element={<GameHub />} />
          <Route path="guides/:gameId/wiki/:title" element={<WikiPage />} />
          <Route path="guides/:gameId/read" element={<Reader />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

import {
  Armchair, Box, CircuitBoard, Cpu, Gamepad2, Gpu, HardDrive, Headphones, Joystick, Keyboard, Laptop,
  MemoryStick, Monitor, Mouse, Package, PlugZap,
} from "lucide-react";

const ICONS = {
  consoles: Gamepad2, gpu: Gpu, cpu: Cpu, motherboard: CircuitBoard, ram: MemoryStick, ssd: HardDrive,
  monitor: Monitor, laptop: Laptop, keyboard: Keyboard, mouse: Mouse, headset: Headphones, controller: Joystick,
  psu: PlugZap, case: Box, chair: Armchair,
};

export default function CategoryIcon({ id, className = "h-5 w-5" }) {
  const Icon = ICONS[id] || Package;
  return <Icon className={className} />;
}

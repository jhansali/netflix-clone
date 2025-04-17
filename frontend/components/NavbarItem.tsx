import React from 'react';
import Link from 'next/link';

interface NavbarItemProps {
  label: string;
  active?: boolean;
  href?: string;
}

const NavbarItem: React.FC<NavbarItemProps> = ({ label, active, href }) => {
  const className = active
    ? 'text-white cursor-default'
    : 'text-gray-200 hover:text-gray-300 cursor-pointer transition';

  // If href is provided, wrap with Link
  if (href) {
    return (
      <Link href={href}>
        <div className={className}>
          {label}
        </div>
      </Link>
    );
  }

  return <div className={className}>{label}</div>;
}

export default NavbarItem;

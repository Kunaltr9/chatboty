import React from 'react'

export const Badge = (props: any) => {
  const { children, className = '' } = props
  return <span className={className} style={{ padding: '2px 6px', borderRadius: 6 }}>{children}</span>
}

export default Badge

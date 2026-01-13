import React from 'react'

export const Button = (props: any) => {
  const { children, onClick, type = 'button', className = '', ...rest } = props
  return (
    <button type={type} onClick={onClick} className={className} {...rest}>
      {children}
    </button>
  )
}

export default Button

import { useEffect, useRef, useState } from 'react';

/** Adds .is-in once the node scrolls into view; unobserves after so it plays once. */
export default function Reveal({ children, delay = 0, className = '', as: Tag = 'div' }) {
  const ref = useRef(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const stop = () => {
      io?.disconnect();
      window.removeEventListener('scroll', onMove);
      window.removeEventListener('resize', onMove);
    };
    // IntersectionObserver never fires while the tab is in the background, so a
    // scroll/resize check runs alongside it: content must not stay invisible.
    const check = () => {
      if (node.getBoundingClientRect().top >= window.innerHeight * 0.88) return false;
      setShown(true);
      stop();
      return true;
    };
    function onMove() {
      check();
    }

    let io;
    if ('IntersectionObserver' in window) {
      io = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setShown(true);
            stop();
          }
        },
        { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }
      );
      io.observe(node);
    }
    window.addEventListener('scroll', onMove, { passive: true });
    window.addEventListener('resize', onMove);
    check();

    return stop;
  }, []);

  return (
    <Tag
      ref={ref}
      className={`reveal ${shown ? 'is-in' : ''} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </Tag>
  );
}

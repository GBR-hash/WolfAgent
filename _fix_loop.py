PATH = r"D:\pycharm projects\WolfAgent\frontend\src\components\Timeline.tsx"
with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('\r\n', '\n')

# Fix the useEffect to only auto-expand once
old_effect = """  // Auto-expand last round when rounds change (game finishes)
  useEffect(() => {
    if (rounds.length > 0 && rounds !== prevRoundsRef.current) {
      prevRoundsRef.current = rounds;
      setExpandedRounds(new Set([rounds[rounds.length - 1]]));
    }
  }, [rounds]);"""

new_effect = """  // Auto-expand last round exactly once when data first loads
  const didAutoExpand = useRef(false);
  useEffect(() => {
    if (rounds.length > 0 && !didAutoExpand.current) {
      didAutoExpand.current = true;
      setExpandedRounds(new Set([rounds[rounds.length - 1]]));
    }
  }, [rounds]);"""

content = content.replace(old_effect, new_effect)

# Remove unused prevRoundsRef
content = content.replace(
    "  const [expandedRounds, setExpandedRounds] = useState<Set<number>>(new Set());\n  const prevRoundsRef = React.useRef<number[]>([]);",
    "  const [expandedRounds, setExpandedRounds] = useState<Set<number>>(new Set());"
)

with open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("Timeline infinite loop fixed")
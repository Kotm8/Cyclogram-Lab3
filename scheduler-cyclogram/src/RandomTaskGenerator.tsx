import type { RandomInputTask } from "./App";


export default function RandomTaskGenerator({ data, setData }: { data: RandomInputTask[], setData: React.Dispatch<React.SetStateAction<RandomInputTask[]>> }) {

    function handleChange(taskIndex: number, possibilityIndex: number, field: keyof RandomInputTask['possibilities'][0], value: number) {
        const newData = [...data];
        newData[taskIndex].possibilities[possibilityIndex][field] = value;
        setData(newData);
    }
    return (
       <div className="p-4">
            <table className="min-w-full border border-gray-300 rounded-lg overflow-hidden text-center">
                <thead className="bg-gray-100">
                    <tr>
                        <th className="px-4border" colSpan={2}>Выполняемые задачи</th>
                        <th className="px-4border" colSpan={2}>Тип команды</th>
                    </tr>
                    <tr>
                        <th className="px-4 text-sm border">Тип задачи</th>
                        <th className="px-4 text-sm border">Вероятность появления задачи, %</th>
                        <th className="px-4 text-sm border">Вероятность появления команды, %</th>
                        <th className="px-4 text-sm border">Длительность, такт</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((task, taskIndex) =>
                        task.possibilities.map((possibility, possibilityIndex) => (
                            <tr key={`${taskIndex}-${possibilityIndex}`}>
                                {possibilityIndex === 0 && (
                                    <>
                                        <td className="px-4 py-2 border" rowSpan={task.possibilities.length}>
                                            {task.name}
                                        </td>
                                        <td className="px-4 py-2 border" rowSpan={task.possibilities.length}>
                                            <input
                                                type="number"
                                                className="w-16 border rounded px-1 text-center"
                                                value={task.chance}
                                                onChange={(e) => {
                                                    const newData = [...data];
                                                    newData[taskIndex].chance = Number(e.target.value);
                                                    setData(newData);
                                                }}
                                            />
                                        </td>
                                    </>
                                )}
                                <td className="px-4 py-2 border">
                                    <input
                                        type="number"
                                        className="w-16 border rounded px-1 text-center"
                                        value={possibility.chance}
                                        onChange={(e) =>
                                            handleChange(taskIndex, possibilityIndex, 'chance', Number(e.target.value))
                                        }
                                    />
                                </td>
                                <td className="px-4 py-2 border">
                                    <input
                                        type="number"
                                        className="w-16 border rounded px-1 text-center"
                                        value={possibility.length}
                                        onChange={(e) =>
                                            handleChange(taskIndex, possibilityIndex, 'length', Number(e.target.value))
                                        }
                                    />
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>

            
        </div>
    );
}